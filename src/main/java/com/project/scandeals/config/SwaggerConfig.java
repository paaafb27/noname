package com.project.scandeals.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;

@Configuration
public class SwaggerConfig {

	@Bean
	public OpenAPI openAPI() {
		// JWT 보안 스키마 정의
		SecurityScheme securityScheme = new SecurityScheme()
				.type(SecurityScheme.Type.HTTP)
				.scheme("bearer")
				.bearerFormat("JWT")
				.in(SecurityScheme.In.HEADER)
				.name("Authorization");
		
		SecurityRequirement securityRequirement = new SecurityRequirement()
				.addList("bearerAuth");
		
		return new OpenAPI()
				.info(new Info()
						.title("scanDeals API")
						.description("세일정보 커뮤니티 API")
						.version("1.0.0")
						.contact(new Contact()
								.name("scanDeals")
								.url("https://github.com/pastry002/scandeals")))
				.components(new Components()
						.addSecuritySchemes("bearerAuth", securityScheme))
				.addSecurityItem(securityRequirement);
	}
}
