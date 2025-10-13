package com.project.scandeals.redis;

import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class RedisService {
	
	private final RedisTemplate<String, String> redisTemplate;
	private final ObjectMapper mapper;
	
	/**
	 * 세일 목록 캐싱
	 */
	public <T> void cacheSaleList(String key, List<T> data, long timeout, TimeUnit unit) {
		
		try {
			String json = mapper.writeValueAsString(data);
			redisTemplate.opsForValue().set(key, json, timeout, unit);
			log.debug("Redis 캐시 저장 : key={}", key);
			
		} catch (JsonProcessingException e) {
			log.error("Redis 캐시 저장 실패 : key={}", key, e);
		}
	}
	
	/**
	 * 세일 목록 조회
	 */
	public <T> List<T> getCachedSaleList(String key, TypeReference<List<T>> typeRef) {
		
		try {
			String cached = redisTemplate.opsForValue().get(key);
			if (cached != null) {
				log.debug("Redis 캐시 HIT : key={}", key);
				return mapper.readValue(cached, typeRef);
			}
		} catch (JsonProcessingException e) {
            log.error("Redis 캐시 조회 실패 : key={}", key, e);
		}
		
		log.debug("Redis 캐시 MISS : key={}", key);
        return null;
	}
	
	/**
	 * 캐시 삭제
	 */
	public void deleteCache(String key) {
		
		redisTemplate.delete(key);
		log.debug("Redis 캐시 삭제 : key={}", key);
	}
	
	/**
	 * 패턴으로 캐시 삭제
	 */
	public void deleteCacheByPattern(String pattern) {
		
		Set<String> keys = redisTemplate.keys(pattern);
		
		if (keys != null && !keys.isEmpty()) {
	        redisTemplate.delete(keys);
            log.debug("Redis 캐시 삭제 : pattern={}, count={}", pattern, keys.size());
	    }
	}
	
}
