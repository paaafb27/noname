package com.project.scandeals.domain.sale.dto;

import java.time.LocalDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonFormat;

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
	
	private List<String> sourcesSiteList;
	private Long CategoryId;
	private String keyword;
	private String sortBy = "latest";
	private String direction = "DESC";
	@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
	private LocalDateTime createdAt;
}
