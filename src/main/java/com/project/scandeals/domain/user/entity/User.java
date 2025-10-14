package com.project.scandeals.domain.user.entity;

import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import com.project.scandeals.common.entity.AuthProvider;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)  // JPA 기본 생성자 (외부 직접 생성 방지)
@AllArgsConstructor
@Builder
@EntityListeners(AuditingEntityListener.class)  // 생성/수정일시 자동 관리
public class User {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;
	
	@Column(nullable = false, unique = true, length = 255)
	private String email;
	
	/** 사용자 이름 */
	@Column(nullable = false, length = 50)
	private String name;
	
	/** 닉네임 */
	@Column(nullable = false, length = 50)
	private String nickname;
	
//	@Column(length = 500)
//	private String profileImage;
	
	/** OAuth 제공자 */
	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 20)
	private AuthProvider provider;
	
	/** OAuth 제공자에서 제공하는 고유 ID */
	@Column(nullable = false, length = 255)
	private String providerId;
	
	/** 생성일 */
	@CreationTimestamp
	@Column(nullable = false, updatable = false)
	private LocalDateTime createdAt;
	
	/** 수정일 */
	@CreationTimestamp
	@Column(nullable = false, updatable = false)
	private LocalDateTime updatedAt;
	
	/**
     * 사용자 정보 업데이트
     * 
     * OAuth 로그인 시 사용자 정보 동기화
     */
    public void updateInfo(String name) {
        this.name = name;
//        this.profileImage = profileImage;
    }
	
	/**
     * 닉네임 변경
     * @param nickname
     */
	public void updateNickName(String nickName) {
		this.nickname = nickName;
	}
	
}
