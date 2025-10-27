package com.project.scandeals.domain.sale.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.project.scandeals.common.dto.PageResponseDTO;
import com.project.scandeals.domain.sale.dto.SaleDTO;
import com.project.scandeals.domain.sale.dto.SaleSearchRequestDTO;
import com.project.scandeals.domain.sale.service.SaleService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/sales")
@RequiredArgsConstructor
public class SaleController {
	
	private final SaleService saleService;
	
	/**
	 * 세일 목록 조회
	 */
	@GetMapping
	public ResponseEntity<PageResponseDTO<SaleDTO>> getSaleList(
			@ModelAttribute SaleSearchRequestDTO requestDto) {
		
		// 필터 검색 여부
		if (isFiltered(requestDto) ) {
			// 조건 검색
			return ResponseEntity.ok(saleService.getFilteredSaleList(requestDto));			
		} else {
			// 최신 검색
			return ResponseEntity.ok(saleService.getSaleList(requestDto));
		}
	}
	
	// 필터링 조건 검사
	private boolean isFiltered(SaleSearchRequestDTO requestDto) {
		
		// 제목 조회
		if (requestDto.getKeyword() != null && !requestDto.getKeyword().isBlank()) {
			return true;
		}
				
		// 출처 사이트
		if (requestDto.getSourcesSiteList() != null && !requestDto.getSourcesSiteList().isEmpty()) {
			return true;
		}
				
		// 가격 범위
		if (requestDto.getMinPrice() != null && requestDto.getMinPrice() > 0) {
			return true;
		}
		
		if (requestDto.getMaxPrice() != null && requestDto.getMaxPrice() < 100000) {
			return true;
		}
		        
		// 정렬 기준 변경 시
		if (!"latest".equals(requestDto.getSortBy())) {
			return true;
		}
				
		return false;
	}
	
	/**
	 * 세일 상세 조회
	 */
	@GetMapping("/{saleId}")
	public ResponseEntity<SaleDTO> getSale(@PathVariable Long saleId) {
		return ResponseEntity.ok(saleService.getSaleDetail(saleId));
	}
	
}
