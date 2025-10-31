package com.project.scandeals.crawl.dto;


import java.time.LocalDateTime;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonFormat;

import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class CrawlDataDTO {

	private String site;
	private List<SaleItem> items;
	
	@Getter
	@NoArgsConstructor
	public static class SaleItem {
		
		/** 제목 */
        private String title;
        
        /** 가격 */
        private String price;
        
        /** 배송비 */
        private String shippingFee;
        
        /** 판매처 */
        private String storeName;
        
        /** 카테고리 */
        private String category;
        
        /** 상품 URL */
        private String productUrl;
        
        /** 이미지 URL */
        private String imageUrl;
        
        /** 출처 사이트 */
        private String sourceSite;
        
        /** 댓글 수 */
        private Integer replyCount;
        
        /** 추천 수 */
        private Integer likeCount;
        
        /** 등록 시간 */
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime createdAt;
	}
}
