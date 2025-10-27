package com.project.scandeals.domain.sale.service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.type.TypeReference;
import com.project.scandeals.common.dto.PageResponseDTO;
import com.project.scandeals.domain.sale.dto.SaleDTO;
import com.project.scandeals.domain.sale.dto.SaleSearchRequestDTO;
import com.project.scandeals.domain.sale.entity.Sale;
import com.project.scandeals.domain.sale.repository.SaleRepository;
import com.project.scandeals.domain.sale.repository.SaleSearchCriteria;
import com.project.scandeals.redis.RedisService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class SaleService {
	
	private final SaleRepository saleRepository;
	private final RedisService redisService;
	private static final int FIRST_PAGE_COUNT = 20; // 첫 페이지 노출 세일 수 
	private static final int MINUS_HOURS = 24; 		// 조회 수 / 댓글 수 / 좋아요 수 조회 기준 시간
	
	/**
	 * 최신 세일 목록 조회 (필터 X)
	 */
	public PageResponseDTO<SaleDTO> getSaleList(SaleSearchRequestDTO requestDto) {
		
		// 기본 페이지는 Redis 캐시 사용
		if (requestDto.getPage() == 0 && requestDto.getSize() == 20) {
			
			try {
				String cacheKey = "sale:list:latest:" +  FIRST_PAGE_COUNT;
				List<SaleDTO> cached = redisService.getCachedSaleList(
						cacheKey,
	                    new TypeReference<List<SaleDTO>>() {}
				);
				
				if (cached != null) {
					log.info("Redis 캐시 HIT");
					long totalCount = saleRepository.count();
					return PageResponseDTO.of(cached, 0, FIRST_PAGE_COUNT, totalCount);
				}
			} catch (RedisConnectionFailureException e) {
				log.error("Redis 연결 실패", e);
			}
		} 
		
		// Redis 캐시 MISS 또는 다른 페이지 → MySQL 조회
		log.info("DB 직접 조회");
		Pageable pageable = PageRequest.of(
				requestDto.getPage(), 
				requestDto.getSize(),
				Sort.by(Sort.Direction.DESC, "createdAt")
		);
		
		Page<Sale> salePage = saleRepository.findAll(Specification.allOf(), pageable);
		
		return PageResponseDTO.from(salePage.map(SaleDTO::from));
	}
	
	/**
	 * 세일 정보 필터 검색
	 */
	public PageResponseDTO<SaleDTO> getFilteredSaleList(SaleSearchRequestDTO requestDto) {
		
		log.info("DB 직접 조회 (필터 검색)");

		// Specification (동적 쿼리) 생성
		Specification<Sale> spec = Specification.allOf(); // (항상 true)

		// 키워드 검색
		if (requestDto.getKeyword() != null && !requestDto.getKeyword().isBlank()) {
			spec = spec.and(SaleSearchCriteria.searchByTitle(requestDto.getKeyword().trim()));
		}
		
		// 소스 사이트 필터
		if (requestDto.getSourcesSiteList() != null && !requestDto.getSourcesSiteList().isEmpty()) {
			spec = spec.and(SaleSearchCriteria.searchBySourceSite(requestDto.getSourcesSiteList()));
		}

		// 최소 가격 (price 컬럼 기준)
		if (requestDto.getMinPrice() != null && requestDto.getMinPrice() > 0) {
			spec = spec.and(SaleSearchCriteria.searchByMinPrice(requestDto.getMinPrice()));
		}

		// 최대 가격 (price 컬럼 기준)
		if (requestDto.getMaxPrice() != null && requestDto.getMaxPrice() < 10000000) {
			spec = spec.and(SaleSearchCriteria.searchByMaxPrice(requestDto.getMaxPrice()));
		}
		
		// Sort (정렬) 생성
		Sort sort = createSort(requestDto.getSortBy());

		// Pageable 생성
		Pageable pageable = PageRequest.of(requestDto.getPage(), requestDto.getSize(), sort);
		
		// Repository 조회
		Page<Sale> salePage = saleRepository.findAll(spec, pageable);
		
		return PageResponseDTO.from(salePage.map(SaleDTO::from));
	}
	
	/**
	 * Sort 객체 생성 헬퍼
	 */
	private Sort createSort(String sortBy) {
        if (sortBy == null) sortBy = "latest"; // 널 체크
        
		switch (sortBy) {
			case "popular":
				// 인기순 = 좋아요 많은 순 + 최신순
				return Sort.by(Sort.Direction.DESC, "likeCount")
						   .and(Sort.by(Sort.Direction.DESC, "createdAt"));
			case "lowPrice":
				// 낮은 가격순 (price 필드 기준)
				return Sort.by(Sort.Direction.ASC, "price");
			case "highPrice":
				// 높은 가격순 (price 필드 기준)
				return Sort.by(Sort.Direction.DESC, "price");
			case "latest":
			default:
				// 최신순
				return Sort.by(Sort.Direction.DESC, "createdAt");
		}
	}
	
	/**
	 * 세일 정보 상세 조회
	 * 
	 * 상세 페이지 조회 + 조회수 증가
	 */
	@Transactional
	public SaleDTO getSaleDetail(Long saleId) {
		
		Sale sale = saleRepository.findById(saleId)
				.orElseThrow(() -> new IllegalArgumentException("세일정보를 찾을 수 없습니다."));
		
		// 조회수 증가
		sale.increaseViewCount();
		
		return SaleDTO.from(sale);
	}
	
	/**
	 * 인기 세일 조회 (좋아요 순)
	 */
	public PageResponseDTO<SaleDTO> getPopularSales(Pageable pageable) {
		
		LocalDateTime since = LocalDateTime.now().minusHours(MINUS_HOURS);
		Page<Sale> salePage = saleRepository.findPopularSales(since, pageable);

		log.info("인기 세일 조회: {}시간 내 {}건", MINUS_HOURS, salePage.getTotalElements());
		
		return PageResponseDTO.from(salePage.map(SaleDTO::from));
	}
	
	
	/**
	 * 댓글 많은 세일 조회
	 */
	public PageResponseDTO<SaleDTO> getMostCommentedSales(Pageable pageable) {
		
		LocalDateTime since = LocalDateTime.now().minusHours(MINUS_HOURS);
		Page<Sale> salePage = saleRepository.findMostCommentedSales(since, pageable);
		
		log.info("댓글 많은 세일 조회: {}시간 내 {}건", MINUS_HOURS, salePage.getTotalElements());
		
		return PageResponseDTO.from(salePage.map(SaleDTO::from));
	}
	
	/**
	 * 세일 정보 저장
	 * 
	 * 크롤러에서 호출
	 */
	@Transactional
	public Sale saveSale(Sale sale) {
		
		// 중복 체크
		Optional<Sale> isExist = saleRepository.findByProductUrl(sale.getProductUrl());
		
		if (isExist.isPresent()) {
			log.debug("중복 세일 발견 : {}", sale.getProductUrl());
			return isExist.get();
		}
		
		Sale saveSale = saleRepository.save(sale);
        log.info("신규 세일 저장: id={}, title={}", saveSale.getId(), saveSale.getTitle());

		return saveSale;
	}
	
	
	/**
	 * Redis 캐시 업데이트
	 */
	public void updateSaleListCache() {
		
		try {
            Pageable pageable = PageRequest.of(0, FIRST_PAGE_COUNT);

            Page<Sale> latestSalesPage = saleRepository.findAll(Specification.allOf(), pageable);
			List<SaleDTO> saleList = latestSalesPage.getContent().stream()
					.map(SaleDTO::from)
					.collect(Collectors.toList());
			
			String cacheKey = String.format("sale:list:latest:%d", FIRST_PAGE_COUNT);
			redisService.cacheSaleList(cacheKey, saleList, 10, TimeUnit.MINUTES);
			
			log.info("세일 목록 캐시 업데이트 완료 : {}건", saleList.size());
			
		} catch (Exception e) {
			log.error("세일 목록 캐시 업데이트 실패");
		}
	}
	

}
