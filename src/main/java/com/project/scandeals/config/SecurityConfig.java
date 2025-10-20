package com.project.scandeals.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import com.project.scandeals.security.jwt.JwtAuthenticationFilter;
import com.project.scandeals.security.oauth.CustomOAuth2UserService;
import com.project.scandeals.security.oauth.OAuth2SuccessHandler;

import lombok.RequiredArgsConstructor;

/**
 * Spring Security 설정
 * 
 * OAuth + JWT 추가 예정
 */
@Configuration
@EnableWebSecurity
//@RequiredArgsConstructor
public class SecurityConfig {

//    private final CustomOAuth2UserService customOAuth2UserService;
//    private final OAuth2SuccessHandler oAuth2SuccessHandler;
//    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        
        http
            // CSRF 비활성화 (JWT 사용으로 불필요)
            .csrf(csrf -> csrf.disable())
            
         // 모든 요청 허용 (인증 불필요)
            .authorizeHttpRequests(auth -> auth
                .anyRequest().permitAll()
            );
//            
//            // 세션 사용 안 함 (JWT로 Stateless 인증)
//            .sessionManagement(session -> 
//                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
//            
//            // URL별 권한 설정
//            .authorizeHttpRequests(auth -> auth
//                // 공개 API (인증 불필요)
//                .requestMatchers(
//                    "/",                          // 메인 페이지
//                    "/sales/**",                  // 세일 상세 페이지
//                    "/api/sales/**",              // 세일 조회 API
//                    "/api/crawl/**",              // 크롤러 데이터 수신
//                    "/api/health/**",             // 헬스체크
//                    "/actuator/health",           // Spring Actuator 헬스체크 ✅ 추가
//                    "/login",                     // 로그인 페이지
//                    "/oauth/**",                  // OAuth 콜백
//                    "/oauth2/**",                 // OAuth2 관련
//                    "/swagger-ui/**",             // Swagger UI
//                    "/v3/api-docs/**",            // API 문서
//                    "/css/**",                    // 정적 리소스
//                    "/js/**",
//                    "/images/**"
//                ).permitAll()
//                
//                // 인증 필요 API (로그인 사용자만)
//                .requestMatchers(
//                    "/api/comments/**",           // 댓글 작성/수정/삭제
//                    "/api/sales/*/likes"          // 좋아요
//                ).authenticated()
//                
//                // 관리자 전용
//                .requestMatchers("/api/admin/**").hasRole("ADMIN")
//                
//                // 그 외 모든 요청은 인증 필요
//                .anyRequest().authenticated()
//            )
//            
//            // OAuth 2.0 로그인 설정
//            .oauth2Login(oauth -> oauth
//                .userInfoEndpoint(userInfo ->
//                    userInfo.userService(customOAuth2UserService))
//                .successHandler(oAuth2SuccessHandler)
//            )
//            
//            // JWT 필터 추가 (UsernamePasswordAuthenticationFilter 전에 실행)
//            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
            
        
        return http.build();
    }
}