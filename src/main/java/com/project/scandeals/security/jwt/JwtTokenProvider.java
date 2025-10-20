//package com.project.scandeals.security.jwt;
//
//import java.nio.charset.StandardCharsets;
//import java.util.Date;
//
//import javax.crypto.SecretKey;
//
//import org.springframework.beans.factory.annotation.Value;
//import org.springframework.stereotype.Component;
//
//import io.jsonwebtoken.Claims;
//import io.jsonwebtoken.ExpiredJwtException;
//import io.jsonwebtoken.Jwts;
//import io.jsonwebtoken.MalformedJwtException;
//import io.jsonwebtoken.UnsupportedJwtException;
//import io.jsonwebtoken.security.Keys;
//import lombok.extern.slf4j.Slf4j;
//
///**
// * JWT 토큰 생성 및 검증
// */
//@Slf4j
//@Component
//public class JwtTokenProvider {
//    
//    private final SecretKey secretKey;
//    private final long accessTokenValidity;
//    private final long refreshTokenValidity;
//    
//    public JwtTokenProvider(
//        @Value("${jwt.secret}") String secret,
//        @Value("${jwt.access-token-validity}") long accessTokenValidity,
//        @Value("${jwt.refresh-token-validity}") long refreshTokenValidity
//    ) {
//    	// Secret Key 검증
//        if (secret == null || secret.trim().isEmpty()) {
//            throw new IllegalArgumentException("JWT Secret이 설정되지 않았습니다. application.yml 확인 필요");
//        }
//        
//        // Secret Key 길이 검증 (HS256은 최소 256비트 = 32바이트)
//        if (secret.length() < 32) {
//            throw new IllegalArgumentException(
//                "JWT Secret 길이가 부족합니다. 최소 32자 이상이어야 합니다. (현재: " + secret.length() + "자)"
//            );
//        }
//        
//        // SecretKey 생성
//        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
//        this.accessTokenValidity = accessTokenValidity;  // 30분
//        this.refreshTokenValidity = refreshTokenValidity;  // 14일
//    }
//    
//    /**
//     * Access Token 생성
//     * 
//     * 유효 기간: 30분
//     * 용도: API 호출 인증
//     */
//    public String createAccessToken(Long userId, String email) {
//    	
//        Date now = new Date();
//        Date validity = new Date(now.getTime() + accessTokenValidity);
//        
//        return Jwts.builder()
//            .subject(userId.toString())
//            .claim("email", email)
//            .claim("type", "access")
//            .issuedAt(now)
//            .expiration(validity)
//            .signWith(secretKey)
//            .compact();
//    }
//    
//    /**
//     * Refresh Token 생성
//     * 
//     * 유효 기간: 14일
//     * 용도: Access Token 갱신
//     */
//    public String createRefreshToken(Long userId) {
//    	
//        Date now = new Date();
//        Date validity = new Date(now.getTime() + refreshTokenValidity);
//        
//        return Jwts.builder()
//            .subject(userId.toString())
//            .claim("type", "refresh")
//            .issuedAt(now)
//            .expiration(validity)
//            .signWith(secretKey)
//            .compact();
//    }
//    
//    /**
//     * 토큰 검증
//     */
//    public boolean validateToken(String token) {
//        
//    	try {
//            Jwts.parser()
//                .verifyWith(secretKey)
//                .build()
//                .parseSignedClaims(token);
//            return true;
//            
//    	} catch (ExpiredJwtException e) {
//            log.warn("만료된 토큰: {}", e.getMessage());
//        } catch (UnsupportedJwtException e) {
//            log.warn("지원하지 않는 토큰: {}", e.getMessage());
//        } catch (MalformedJwtException e) {
//            log.warn("잘못된 형식의 토큰: {}", e.getMessage());
//        } catch (SecurityException e) {
//            log.warn("서명 검증 실패: {}", e.getMessage());
//        } catch (IllegalArgumentException e) {
//            log.warn("잘못된 토큰 값: {}", e.getMessage());
//        }
//        return false;
//    }
//    
//    /**
//     * 토큰에서 사용자 ID 추출
//     */
//    public Long getUserId(String token) {
//        Claims claims = Jwts.parser()
//            .verifyWith(secretKey)
//            .build()
//            .parseSignedClaims(token)
//            .getPayload();
//        
//        return Long.parseLong(claims.getSubject());
//    }
//    
//    /**
//     * 토큰에서 이메일 추출
//     */
//    public String getEmail(String token) {
//        Claims claims = Jwts.parser()
//            .verifyWith(secretKey)
//            .build()
//            .parseSignedClaims(token)
//            .getPayload();
//        
//        return claims.get("email", String.class);
//    }
//    
//    /**
//     * 토큰 만료 시간 확인
//     */
//    public Date getExpirationDate(String token) {
//        Claims claims = Jwts.parser()
//                .verifyWith(secretKey)
//                .build()
//                .parseSignedClaims(token)
//                .getPayload();
//
//        return claims.getExpiration();
//    }
//}