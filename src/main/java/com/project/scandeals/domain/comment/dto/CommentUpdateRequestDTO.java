package com.project.scandeals.domain.comment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 댓글 수정 요청 DTO
 * 
 * 클라이언트 to 서버
 * 입력값 검증 자동화
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CommentUpdateRequestDTO {
	
	@NotBlank(message = "댓글 내용은 필수입니다.")
	@Size(min = 1, max= 500, message = "댓글은 1자 이상 500자 이하로 입력해주세요")
	private String content;
	
}
