package com.project.scandeals.domain.comment.dto;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

import com.project.scandeals.domain.comment.entity.Comment;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CommentDTO {
	
	private Long id;
    private Long saleId;
    private Long userId;
    private String userNickname;
    private String userProfileImage;
    private Long parentId;
    private String content;
    private Boolean isDeleted;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    // 대댓글 목록
    private List<CommentDTO> replyList;
    
    // Entity -> DTO 변환
    public static CommentDTO from(Comment comment) {
    	
    	if (comment == null) {
    		return null;
    	}
    	
    	return CommentDTO.builder()
    			.id(comment.getId())
    			.saleId(comment.getSale().getId())
    			.userId(comment.getUser().getId())
    			.userNickname(comment.getUser().getNickname())
    			.parentId(comment.getParent() != null ? comment.getParent().getId() : null)
    			.content(comment.getIsDeleted() ? "삭제된 댓글입니다." : comment.getContent())
    			.isDeleted(comment.getIsDeleted())
    			.createdAt(comment.getCreatedAt())
    			.updatedAt(comment.getUpdatedAt())
    			.replyList(comment.getReplyList() != null ? 
    					comment.getReplyList().stream()
    						.map(CommentDTO::from)
    						.collect(Collectors.toList()) : null)
    			.build();
    }
    
    // Entity 리스트 -> DTO 변환
    public static List<CommentDTO> fromList (List<Comment> commentList) {
    	return commentList.stream()
    				.map(CommentDTO::from)
    				.collect(Collectors.toList());
    }
    
}
