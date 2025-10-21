package com.project.scandeals.security.oauth;

import java.util.Map;

import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.project.scandeals.common.entity.AuthProvider;
import com.project.scandeals.domain.user.entity.User;
import com.project.scandeals.domain.user.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * OAuth 2.0 사용자 정보 처리 서비스
 * 
 * Google 로그인 시 사용자 정보 DB 저장
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;
    
    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) 
            throws OAuth2AuthenticationException {
		
    	// 1. OAuth 2.0 사용자 정보 로드
		OAuth2User oAuth2User = super.loadUser(userRequest);
		
		// 2. OAuth 제공자 확인 (Google, Naver, Kakao)
		String registrationId = userRequest.getClientRegistration().getRegistrationId();
        AuthProvider provider = AuthProvider.valueOf(registrationId.toUpperCase());
		
		// 3. 사용자 정보 추출
        Map<String, Object> attributes = oAuth2User.getAttributes();
		String providerId = attributes.get("sub").toString();
		String email = attributes.get("email").toString();
		String name = attributes.get("name").toString();
		
        // 4. DB에서 사용자 조회 또는 생성
		User user = userRepository.findByProviderAndProviderId(provider, providerId)
				.map(existingUser -> {
					existingUser.updateInfo(name);
					return userRepository.save(existingUser);
				})
				.orElseGet(() -> {
					User newUser = User.builder()
							.email(email)
							.name(name)
							.provider(provider)
							.providerId(providerId)
							.build();
					return userRepository.save(newUser);
				});
		
		log.info("OAuth 로그인 성공: userId={}, email={}, provider={}", user.getId(), user.getEmail(), provider);
		
		// 5. CustomOAuth2User 반환 (SecurityContext에 저장됨)
        return new CustomOAuth2User(user, attributes);
	}
	
}
