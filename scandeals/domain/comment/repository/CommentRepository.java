package com.project.scandeals.domain.comment.repository;

import java.util.List;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.project.scandeals.domain.comment.entity.Comment;

public interface CommentRepository extends JpaRepository<Comment, Long>{

	/**
	 * 세일별 댓글 조회
	 */
	@EntityGraph(attributePaths = {"user", "replies", "replies.user"})
	@Query("SELECT c FROM Comment c WHERE c.sale.id = :saleId AND c.parent IS NULL ORDER BY c.createdAt ASC")
	List<Comment> findbySaleIdWithReplies(@Param("saleId") Long saleId);
	
	/**
	 * 세일별 댓글 수
	 */
	long countBySaleId(Long saleId);
}
