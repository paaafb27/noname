package com.project.scandeals.domain.sale.entity;

import java.time.LocalDateTime;

import org.hibernate.annotations.Comment;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import com.project.scandeals.domain.category.entity.Category;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;


@Entity
@Table(
		name = "sales",
		indexes = {
			@Index(name = "idx_created_at", columnList = "created_at DESC"),
			@Index(name = "idx_source_site", columnList = "source_site"),
			@Index(name = "idx_category", columnList = "category_id"),
			@Index(name = "idx_like_count", columnList = "like_count DESC"),
			@Index(name = "idx_view_count", columnList = "view_count DESC")
	},
		uniqueConstraints = {
			@UniqueConstraint(name = "uk_product_url", columnNames = "product_url")
	})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class Sale {

	/** 세일 ID */
	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;
	
	/** 상품명 */
	@Column(nullable = false, length = 500)
	private String title;
	
	/** 가격 */
	@Column(nullable = false)
	private Integer price;
	
	/** 판매처 */
	@Column(name = "store_name", length = 100)
    private String storeName;

	/** 구매링크 */
    @Column(name = "product_url", nullable = false, unique = true, length = 500)
    private String productUrl;

    /** 썸네일 이미지 */
    @Column(name = "image_url", length = 1000)
    private String imageUrl;

    /** 출처 사이트 */
    @Column(name = "source_site", nullable = false, length = 50)
    private String sourceSite;
	
    /** 카테고리 */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;
    
    /** 조회 수 */
    @Column(name = "view_count", nullable = false)
    @Builder.Default  // 기본값 0
    private Integer viewCount = 0;

    /** 좋아요 수 */
    @Column(name = "like_count", nullable = false)
    @Builder.Default
    private Integer likeCount = 0;

    /** 댓글 수 */
    @Column(nullable = false)
    @Builder.Default
    private Integer commentCount = 0;

    /** 활성화 여부 */
    @Column(name = "is_active", nullable = false)
    @Builder.Default
    @Comment("활성화 여부 (현재 미사용)")
    private Boolean isActive = true;  // soft delete용

    /** 생성일시 */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /** 수정일시 */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt ;
    
    /**
     * 조회수 증가
     */
    public void increaseViewCount() {
        this.viewCount++;
    }
    
    /**
     * 엔티티 생성 시 자동으로 생성일시 설정
     */
    @PrePersist
    protected void onCreate() {
    	
    	this.createdAt = LocalDateTime.now();
    	this.updatedAt = LocalDateTime.now();
    }
    
    /**
     * 엔티티 수정 시 자동으로 수정일시 설정
     */
    @PreUpdate
    protected void onUpdate() {

    	this.updatedAt = LocalDateTime.now();
    }

    /**
     * 좋아요 수 업데이트
     */
    public void updateLikeCount(int delta) {
        this.likeCount += delta;
    }

    /**
     * 댓글 수 업데이트
     */
    public void updateCommentCount(int delta) {
        this.commentCount += delta;
    }

    /**
     * 카테고리 변경
     */
    public void updateCategory(Category category) {
        this.category = category;
    }
    
    /**
     * 세일 정보 비활성화
     */
    public void deactivate() {
        this.isActive = false;
    }

    /**
     * 세일 정보 활성화
     */
    public void activate() {
    	this.isActive = true;
    }
	
}
