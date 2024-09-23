package org.datacapstonedesign.backend.delegate;

import java.util.List;
import org.datacapstonedesign.backend.generated.api.ArticleInfosApiDelegate;
import org.datacapstonedesign.backend.generated.dto.CompaniesResponse;
import org.datacapstonedesign.backend.generated.dto.SearchResponse;
import org.datacapstonedesign.backend.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

@Service
public class ArticleInfosApiDelegateImpl implements ArticleInfosApiDelegate {
    private final SearchService searchService;

    @Autowired
    public ArticleInfosApiDelegateImpl(SearchService searchService){
        this.searchService = searchService;
    }

    @Override
    public ResponseEntity<SearchResponse> getArticleInfos(
        final String xUserID,
        final List<String> hashtags,
        final String company,
        final String query,
        final Integer page,
        final Integer size
    ) {
        // TODO - implement logging
        return ResponseEntity.ok(
            new SearchResponse()
                .status(200)
                .message("ok")
                .content(searchService.getArticleInfos(hashtags, company, query, page, size))
        );
    }

    @Override
    public ResponseEntity<CompaniesResponse> getCompanyNames(final String xUserID) {
        // TODO - implement logging and concrete functionality
        return ArticleInfosApiDelegate.super.getCompanyNames(xUserID);
    }
}
