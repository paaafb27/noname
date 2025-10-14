package com.project.scandeals.domain.sale.dto;

import com.project.scandeals.common.entity.SourceSite;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 세일 검색 DTO
 * 
 * 조회 시 필터링 파라미터
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SaleSearchRequestDTO {

	@Min(value = 0, message = "페이지는 0 이상이어야 합니다.")
	private int page = 0;
	
	@Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다.")
	private int size = 20;
	
	private SourceSite sourceSite;
	private Long CategoryId;
	private String keyword;
	private String sortBy = "createdAt";
	private String direction = "DESC";
}
