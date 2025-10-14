package com.project.scandeals.common.entity;

public enum SourceSite {
	PPOMPPU("뽐뿌"),
	RULIWEB("루리웹"),
	ARCALIVE("아카라이브"),	
	FMKOREA("에펨코리아"),	
	QUASARZONE("퀘이사존"),	
//    CLIEN("클리앙"),
    EOMISAE("어미새");
	
	private final String displayName;
	
	SourceSite(String displayName) {
		this.displayName = displayName;
	}
	
	public String getDisplayName() {
		return displayName;
	}
}
