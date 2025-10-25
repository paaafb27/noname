package com.project.scandeals.crawl.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.project.scandeals.crawl.dto.CrawlDataDTO;
import com.project.scandeals.domain.sale.entity.Sale;
import com.project.scandeals.domain.sale.service.SaleService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RestController
@RequestMapping("/api/crawl")
@RequiredArgsConstructor
public class CrawlDataController {

	private final SaleService saleService;
	
	@Value("${app.crawl.api-key}")
	private String apiKey;
	
	/**
	 * 크롤링 데이터 수신
	 */
	@PostMapping("/data")
	public ResponseEntity<?> receiveCrawlData (
			@RequestHeader("X-API-Key") String requestApiKey,
			@RequestBody CrawlDataDTO crawlDataDTO
	) {
		// API Key 검증
		if (!apiKey.equals(requestApiKey)) {
			log.warn("크롤링 API 인증 실패");
			return ResponseEntity.status(401).body("Unauthorized");
		}
		
		int savedCount = 0;
		int skippedCount = 0;
		
		for (CrawlDataDTO.SaleItem item : crawlDataDTO.getItems()) {
			try {
				Sale sale = Sale.builder()
						.title(item.getTitle())
	                    .price_str(item.getPriceStr())
	                    .storeName(item.getStoreName())
	                    .productUrl(item.getProductUrl())
	                    .imageUrl(item.getImageUrl())
	                    .sourceSite(item.getSourceSite())
	                    .build();
				
				saleService.saveSale(sale);
                savedCount++;
                
			} catch (Exception e) {
				log.error("세일 저장 실패: {}", item.getTitle(), e);
                skippedCount++;
			}
		}
		
		// Redis 캐시 업데이트
		saleService.updateSaleListCache();
		
		log.info("크롤링 완료: site={}, saved={}, skipped={}", 
				crawlDataDTO.getSite(), savedCount, skippedCount);
		
		return ResponseEntity.ok(
	            String.format("Saved: %d, Skipped: %d", savedCount, skippedCount));
				
	}
	
	/**
     * 헬스체크
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Crawl API OK");
    }
	
	
}
