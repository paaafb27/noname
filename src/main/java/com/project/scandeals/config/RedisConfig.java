package com.project.scandeals.config;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * Redis 캐시
 * 
 * 목적 :
 * - 자주 조회되는 데이터 캐싱
 * - 세션 저장
 * - 조회 수 등 카운터 관리
 * 
 * 캐시 전략 :
 * - 세일 목록 : 10분
 * - 세일 상세 : 10분
 * - 카테고리 : 1일 
 */
@Configuration
@EnableCaching // 스프링 캐시
public class RedisConfig {

	/**
	 * Redis 템플릿 설정
	 * 
	 * Redis에 직접 데이터 저장 / 조회
	 */
	
	@Bean
	public RedisTemplate<String, String> redisTemplate(RedisConnectionFactory connectionFactory) {
		
		RedisTemplate<String, String> template = new RedisTemplate<>();
		template.setConnectionFactory(connectionFactory);
		
		// key는 String으로 직렬화
		template.setKeySerializer(new StringRedisSerializer());
		template.setHashKeySerializer(new StringRedisSerializer());
		
		// value는 JSON으로 직렬화
		template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
		template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());
	
		template.afterPropertiesSet();
		
		return template;
	}
	
	@Bean
	public ObjectMapper objectMapper() {
		
		ObjectMapper mapper = new ObjectMapper();
		
		mapper.registerModule(new JavaTimeModule());
		mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
		
		return mapper;
	}
		
	
}
