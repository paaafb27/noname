package com.project.scandeals.domain.comment.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.project.scandeals.domain.comment.dto.CommentCreateRequest;
import com.project.scandeals.domain.comment.dto.CommentDTO;
import com.project.scandeals.domain.comment.entity.Comment;
import com.project.scandeals.domain.comment.repository.CommentRepository;
import com.project.scandeals.domain.sale.entity.Sale;
import com.project.scandeals.domain.sale.repository.SaleRepository;
import com.project.scandeals.domain.user.entity.User;
import com.project.scandeals.domain.user.repository.UserRepository;
import com.project.scandeals.redis.RedisService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CommentService {
	
	private final CommentRepository commentRepository;
	private final SaleRepository saleRepository;
	private final UserRepository userRepository;
	private final RedisService redisService;
	
	/**
	 * 댓글 목록 조회
	 */
	public List<CommentDTO> getCommentList(Long saleId) {
		
		List<Comment> commentList = commentRepository.findbySaleIdWithReplies(saleId);
		
		return commentList.stream()
				.map(CommentDTO::from)
				.collect(Collectors.toList());
	}
	
	/**
	 * 댓글 작성
	 */
	@Transactional
	public CommentDTO createComment (Long saleId, Long userId, CommentCreateRequest request) {
		
		Sale sale = saleRepository.findById(saleId)
				.orElseThrow(() -> new IllegalArgumentException("세일정보를 찾을 수 없습니다."));
		
		User user = userRepository.findById(userId)
				.orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
		
		// 대댓글인 경우 부모 조회
		Comment parent = null;
		if (request.getParentId() != null) {
			parent = commentRepository.findById(request.getParentId())
					.orElseThrow(() -> new IllegalArgumentException("부모 댓글을 찾을 수 없습니다."));
		}
		
		Comment comment = Comment.builder()
				.sale(sale)
	            .user(user)
	            .parent(parent)
	            .content(request.getContent())
	            .build();
		
		commentRepository.save(comment);
		
		// 세일 댓글 증가
		sale.updateCommentCount(1);
		
		// Redis 캐시 무효화
		redisService.deleteCache("sale:id:" + saleId);
		
		log.info("댓글 작성 완료: commentId={}, saleId={}, user={}, content={}",
	            comment.getId(),
	            saleId,
	            comment.getUser().getNickname(),
	            comment.getContent().substring(0, Math.min(20, comment.getContent().length())) + "..."
	        );
		
		return CommentDTO.from(comment);
	}
	
	/**
	 * 댓글 삭제
	 */
	@Transactional
	public void deleteComment(Long commentId, Long userId) {
		
		Comment comment = commentRepository.findById(commentId)
				.orElseThrow(() -> new IllegalArgumentException("댓글을 찾을 수 없습니다."));
		
		if (!comment.getUser().getId().equals(userId)) {
			throw new IllegalArgumentException("댓글 작성자만 삭제할 수 있습니다.");
		}
		
		comment.delete();
		
		// 세일 댓글 개수 감소
		comment.getSale().updateCommentCount(-1);
		
		// Redis 캐시 무효화
        redisService.deleteCache("sale:id:" + comment.getSale().getId());
		
		log.info("댓글 삭제 : commentId={}, user={}", commentId, userId);
	}
	
}
