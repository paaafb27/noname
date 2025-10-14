package com.project.scandeals.security.oauth;

import java.util.Map;
import java.util.Optional;

import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import com.project.scandeals.common.entity.AuthProvider;
import com.project.scandeals.domain.user.entity.User;
import com.project.scandeals.domain.user.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService{

	private final UserRepository userRepository;
	
	@Override
	public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
		
		OAuth2User oAuth2User = super.loadUser(userRequest);
		
		String registrationId = userRequest.getClientRegistration().getRegistrationId();
		AuthProvider provider = AuthProvider.valueOf(registrationId.toUpperCase());
		
		Map<String, Object> attributes = oAuth2User.getAttributes();
		
		String providerId = attributes.get("sub").toString();
		String email = attributes.get("email").toString();
		String name = attributes.get("name").toString();
//		String profileImage = attributes.get("picture").toString();
		
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
		log.info("OAuth 로그인 성공 : userId={}, email={}", user.getId(), user.getEmail());
		
		return new CustomOAuth2User(user, attributes);
	}
	
}
