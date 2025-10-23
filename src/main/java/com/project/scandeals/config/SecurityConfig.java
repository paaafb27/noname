package com.project.scandeals.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

import com.project.scandeals.security.oauth.CustomOAuth2UserService;
import com.project.scandeals.security.oauth.OAuth2SuccessHandler;

import lombok.RequiredArgsConstructor;

/**
 * Spring Security 설정
 * 
 * OAuth 2.0 + 세션 기반 인증
 * 효과: 빠른 구현, 안정적 인증
 * 
 * OAuth + JWT 추가 예정
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

	private final CustomOAuth2UserService customOAuth2UserService;
    private final OAuth2SuccessHandler oAuth2SuccessHandler;
//    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        
        http
            // CSRF 비활성화 (JWT 사용으로 불필요)
            .csrf(csrf -> csrf.disable())
            
            // 세션 정책 (IF_REQUIRED: 필요 시 세션 생성)
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
                    .maximumSessions(1)  // 동시 세션 1개
                    .maxSessionsPreventsLogin(false))  // 새 로그인 시 기존 세션 만료
            
            // URL별 권한 설정
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                    "/",                          	// 메인 페이지
                    "/sales/**",                  	// 세일 상세 페이지
                    "/api/sales/**",              	// 세일 조회 API
                    "/api/sales/{saleId}",        	// 세일 조회 API
                    "/api/comments/sale/**",		// 댓글 목록 조회
                    "/api/crawl/**",              	// 크롤러 데이터 수신
                    "/login",                     	// 로그인 페이지
                    "/oauth/**",                  	// OAuth 콜백
                    "/oauth2/**",                 	// OAuth2 관련
                    "/swagger-ui/**",             	// Swagger UI
                    "/v3/api-docs/**",            	// API 문서
//                    "/api/health/**",             // 헬스체크
//                    "/actuator/health",           // Spring Actuator 헬스체크
                    "/css/**",                    	// 정적 리소스
                    "/js/**",
                    "/images/**"
                ).permitAll()
                
                // 인증 필요 API (로그인 사용자만)
                .requestMatchers(
                    "/api/comments/**",           // 댓글 작성/수정/삭제
                    "/api/sales/*/likes"          // 좋아요
                ).authenticated()
                
                // 그 외 모든 요청은 인증 필요
                .anyRequest().authenticated()
             )
//                
//                // 관리자 전용
//                .requestMatchers("/api/admin/**").hasRole("ADMIN")
//            )
//            
            // OAuth 2.0 로그인 설정
            .oauth2Login(oauth -> oauth
            	.loginPage("/login")
                .userInfoEndpoint(userInfo ->
                    userInfo.userService(customOAuth2UserService))
                .successHandler(oAuth2SuccessHandler)
            )
//            
//            // JWT 필터 추가 (UsernamePasswordAuthenticationFilter 전에 실행)
//            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
                
            .logout(logout -> logout
            	.logoutUrl("/logout")
                .logoutSuccessUrl("/")
                .invalidateHttpSession(true)
                .deleteCookies("JSESSIONID")
            );
                
        return http.build();
    }
}