package com.project.scandeals.crawl.dto;


import java.util.List;

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
        
        /** 판매처 */
        private String storeName;
        
        /** 판매처 */
        private String category;
        
        /** 상품 URL */
        private String productUrl;
        
        /** 이미지 URL */
        private String imageUrl;
        
        /** 출처 사이트 */
        private String sourceSite;
        
        /** 배송비 */
        private String shippingFee;
        
        /** 댓글 수 */
        private Integer replyCount;
        
        /** 추천 수 */
        private Integer likeCount;
        
        /** 크롤링 시간 */
        private String crawledAt;
	}
}
