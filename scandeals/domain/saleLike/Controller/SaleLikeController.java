package com.project.scandeals.domain.saleLike.Controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.project.scandeals.domain.saleLike.service.SaleLikeService;

import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/sales/{saleId}/likes")
@RequiredArgsConstructor
public class SaleLikeController {
	
	private final SaleLikeService saleLikeService;
	
	/**
	 * 좋아요 토글
	 */
	@PostMapping
	public ResponseEntity<Boolean> toggleLike(
			@PathVariable Long saleId,
	        @AuthenticationPrincipal Long userId
			) {
		boolean liked = saleLikeService.toggleLike(saleId, userId);
		return ResponseEntity.ok(liked);
	}
	
	/**
	 * 좋아요 여부 확인
	 */
	@GetMapping
    public ResponseEntity<Boolean> isLiked(
        @PathVariable Long saleId,
        @AuthenticationPrincipal Long userId
    ) {
        return ResponseEntity.ok(saleLikeService.isLiked(saleId, userId));
    }
	
	
}
