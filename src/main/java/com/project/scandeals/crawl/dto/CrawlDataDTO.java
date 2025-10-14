package com.project.scandeals.crawl.dto;

import java.math.BigDecimal;
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
		
		private String title;
        private Integer price;
        private String storeName;
        private String productUrl;
        private String imageUrl;
        private String sourceSite;
	}
}
