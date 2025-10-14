package com.project.scandeals.common.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * API 응답 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ApiResponseDTO<T> {

	private boolean success;
	private String message;
	private T data;
	
	/**
	 * 성공 응답
	 */
	public static <T> ApiResponseDTO<T> success (T data) {
		
		return ApiResponseDTO.<T>builder()
				.success(true)
				.message("요청이 성공했습니다.")
				.data(data)
				.build();
	}
	
	/**
	 * 실패 응답
	 */
	public static <T> ApiResponseDTO<T> fail(String message) {
		
		return ApiResponseDTO.<T>builder()
				.success(true)
				.message(message)
				.data(null)
				.build();
	}
}
