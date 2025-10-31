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
import lombok.extern.slf4j.Slf4j;

@Slf4j
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
		
		log.info("세일 목록 조회 요청: {}", requestDto);
		
		boolean hasFilter = 
				(requestDto.getKeyword() != null && !requestDto.getKeyword().isBlank()) ||
		        (requestDto.getSourcesSiteList() != null && !requestDto.getSourcesSiteList().isEmpty()) ||
		        (requestDto.getCategoryId() != null) ||
		        (requestDto.getPage() > 0) ||
		        (!"latest".equals(requestDto.getSortBy()));
		
		PageResponseDTO<SaleDTO> responseDTO;
		
		if (hasFilter) {
	        log.info("필터링 검색 실행");
	        responseDTO = saleService.getFilteredSaleList(requestDto);
	    } else {
	        log.info("기본 목록 조회 (캐시 가능)");
	        responseDTO = saleService.getSaleList(requestDto);
	    }
		
	    return ResponseEntity.ok(responseDTO);

	}

	
	/**
	 * 세일 상세 조회
	 */
	@GetMapping("/{saleId}")
	public ResponseEntity<SaleDTO> getSale(@PathVariable Long saleId) {
		return ResponseEntity.ok(saleService.getSaleDetail(saleId));
	}
	
}
