package com.project.scandeals.domain.comment.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.project.scandeals.domain.comment.dto.CommentCreateRequestDTO;
import com.project.scandeals.domain.comment.dto.CommentDTO;
import com.project.scandeals.domain.comment.service.CommentService;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@RestController
@RequestMapping("/api/sales/{saleId}/comments")
public class CommentController {

	private CommentService commentService;
	
	/**
	 * 댓글 목록 조회
	 */
	@GetMapping
	public ResponseEntity<List<CommentDTO>> getCommentList(@PathVariable Long saleId) {
		return ResponseEntity.ok(commentService.getCommentList(saleId));
	}
	
	/**
	 * 댓글 작성
	 */
	@PostMapping
	public ResponseEntity<CommentDTO> createComment (
			@PathVariable Long saleId,
			@AuthenticationPrincipal Long userId,
			@RequestBody CommentCreateRequestDTO request){
		return ResponseEntity.ok(commentService.createComment(saleId, userId, request));
	}
	
	/**
	 * 댓글 삭제
	 */
	@DeleteMapping("/{commentId}")
	public ResponseEntity<Void> deleteComment(
			@PathVariable Long saleId,
	        @PathVariable Long commentId,
	        @AuthenticationPrincipal Long userId) {
		commentService.deleteComment(commentId, userId);
		return ResponseEntity.noContent().build(); 
	}
}
