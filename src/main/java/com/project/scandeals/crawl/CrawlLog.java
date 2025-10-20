package com.project.scandeals.crawl;

import java.time.LocalDateTime;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "crawl_logs")
public class CrawlLog {

	@Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String siteName;
    private Integer totalItems;      	// 총 수집 수
    private Integer newItems;        	// 신규 저장 수
    
    private Integer noPriceItems;    	// 가격 정보 없는 수
    private Integer noCommentItems;  	// 댓글 정보 없는 수
    
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
}
