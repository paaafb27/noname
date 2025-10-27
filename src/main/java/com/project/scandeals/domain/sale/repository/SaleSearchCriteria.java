package com.project.scandeals.domain.sale.repository;

import java.util.List;

import org.springframework.data.jpa.domain.Specification;

import com.project.scandeals.domain.sale.entity.Sale;

/**
 * Sale 엔티티 동적 쿼리 정의
 */
public class SaleSearchCriteria {

	/**
	 * 제목
	 */
	public static Specification<Sale> searchByTitle(String keyword) {
		return (root, query, cb) ->
			cb.like(root.get("title"), "%" + keyword + "%");
	}
	
	/**
     * 출처 사이트
     */
    public static Specification<Sale> searchBySourceSite(List<String> sourceSiteList) {
        return (root, query, cb) -> root.get("sourceSite").in(sourceSiteList);
    }

    /**
     * 최소 가격 (>=)
     */
    public static Specification<Sale> searchByMinPrice(Integer minPrice) {
        // Sale.price 필드 (숫자 타입)
        return (root, query, cb) -> 
            cb.greaterThanOrEqualTo(root.get("price"), minPrice);
    }

    /**
     * 최대 가격 (<=)
     */
    public static Specification<Sale> searchByMaxPrice(Integer maxPrice) {
        return (root, query, cb) -> 
            cb.lessThanOrEqualTo(root.get("price"), maxPrice);
    }
}
