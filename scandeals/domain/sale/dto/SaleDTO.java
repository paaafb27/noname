package com.project.scandeals.domain.sale.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import com.project.scandeals.domain.sale.entity.Sale;

import lombok.Builder;
import lombok.Getter;

/**
 * 세일 DTO
 * 
 * Service <> Controller 데이터 전달
 * Entity 직접 노출 방지
 */
@Getter
@Builder
public class SaleDTO {

	private Long id;						/** 세일 아이디 */
	private String title;					/** 세일 제목 */
	private Integer price;					/** 가격 */
	private String storeName;				/** 판매처 */
	private String productUrl;				/** 상품 url */
	private String imageUrl;				/** 이미지 url */
	private String sourceSite;				/** 출처 사이트 */
	private Long categoryId;				/** 카테고리 ID */
	private String categoryName;			/** 카테고리 이름 */
	private Integer viewCount;				/** 조회 수 */
	private Integer likeCount;				/** 좋아요 수 */
	private Integer commentCount;			/** 댓글 수 */
	private LocalDateTime createdAt;		/** 등록일 */
	
	/**
     * Entity → DTO 변환
     */
	public static SaleDTO from(Sale sale) {
		
		if (sale == null) {
			return null;
		}
		
		return SaleDTO.builder()
				.id(sale.getId())
				.title(sale.getTitle())
				.price(sale.getPrice())
				.storeName(sale.getStoreName())
				.productUrl(sale.getProductUrl())
				.imageUrl(sale.getImageUrl())
				.sourceSite(sale.getSourceSite())
				.categoryId(sale.getCategory() != null ? sale.getCategory().getId() : null)
                .categoryName(sale.getCategory() != null ? sale.getCategory().getName() : null)
				.viewCount(sale.getViewCount())
				.likeCount(sale.getLikeCount())
	            .commentCount(sale.getCommentCount())
	            .createdAt(sale.getCreatedAt())
	            .build();
	}
}
