package com.project.scandeals.common.dto;

import java.time.LocalDateTime;
import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 에러 응답 DTO
 * 
 * 예외 발생 시 상세 정보 제공
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorResponseDTO {

	private LocalDateTime timestamp;
	private int status;
	private String error;
	private String message;
	private String path;
	private List<FieldError> errors;
	
	@Data
	@Builder
	@NoArgsConstructor
	@AllArgsConstructor
	public static class FieldError {
		
		private String field;
		private String message;
		private Object rejectedValue;
	}
}
