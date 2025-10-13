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
			@ModelAttribute SaleSearchRequestDTO request) {
		return ResponseEntity.ok(saleService.getSaleList(request));
	}
	
	/**
	 * 세일 상세 조회
	 */
	@GetMapping("/{saleId}")
	public ResponseEntity<SaleDTO> getSale(@PathVariable Long saleId) {
		return ResponseEntity.ok(saleService.getSaleDetail(saleId));
	}
	
}
