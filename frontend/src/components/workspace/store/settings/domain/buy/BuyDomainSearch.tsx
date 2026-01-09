'use client';

import React, { useState } from 'react';
import { useLazyQuery } from '@apollo/client/react';
import { useRouter, useParams } from 'next/navigation';
import { SearchDomainsDocument } from '@/services/graphql/domains/queries/purchases/__generated__/searchDomains.generated';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Badge } from '@/components/shadcn-ui/badge';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Globe, Search, CheckCircle2, AlertCircle, ChevronLeft, ChevronRight, ArrowLeft } from 'lucide-react';

export function BuyDomainSearch() {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspace_id as string;

  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const [searchDomains, { data, loading, error }] = useLazyQuery(SearchDomainsDocument, {
    fetchPolicy: 'network-only', // Always fetch fresh data, don't use cache
  });

  const handleSearch = async (e?: React.FormEvent, page = 1) => {
    if (e) {
      e.preventDefault();
    }

    if (!searchQuery.trim()) {
      return;
    }

    await searchDomains({
      variables: {
        query: searchQuery.trim(),
        page,
        pageSize: 10,
      },
    });
    setCurrentPage(page);
  };

  const handleBuyDomain = (domain: string) => {
    router.push(
      `/workspace/${workspaceId}/store/settings/domains/buy/confirm/${encodeURIComponent(domain)}`
    );
  };

  const searchResults = data?.searchDomains;
  const suggestions = searchResults?.suggestions?.filter(Boolean) || [];
  const suggestedDomains = suggestions.slice(0, 3);
  const otherExtensions = suggestions.slice(3);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/workspace/${workspaceId}/store/settings/domains`)}
          className="md:hidden"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <Globe className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-xl sm:text-2xl font-bold">Buy new domain</h1>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Find the perfect domain</CardTitle>
          <p className="text-sm text-muted-foreground">
            Purchase, host, and manage your domain all in one place with Huzilerz
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="them.com"
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="bg-black hover:bg-black/90 text-white px-6 w-full sm:w-auto"
            >
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
          </form>

          {/* Availability Message */}
          {searchResults && (
            <div className="mt-4">
              {searchResults.available ? (
                <Alert className="bg-green-50 border-green-200">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-900">
                    {searchResults.query} is available!
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {searchResults.query} isn't available. Choose a suggested domain below or search again.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to search domains: {error.message}</AlertDescription>
        </Alert>
      )}

      {/* Search Results */}
      {searchResults && !loading && (
        <div className="space-y-6">
          {/* Suggested Domains */}
          {suggestedDomains.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle className="text-lg">You might like these</CardTitle>
                </div>
                <Badge variant="outline" className="w-fit mt-2">Suggested</Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                {suggestedDomains.map((domain, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-3 border-b last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium">{domain?.domain}</p>
                        <p className="text-sm text-muted-foreground">
                          ${domain?.priceUsd.toFixed(2)} USD / year
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => domain?.domain && handleBuyDomain(domain.domain)}
                      variant="outline"
                      className="px-6"
                    >
                      Buy
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Other Extensions */}
          {otherExtensions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Other extensions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {otherExtensions.map((domain, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-3 border-b last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <div>
                        <p className="font-medium">{domain?.domain}</p>
                        <p className="text-sm text-muted-foreground">
                          ${domain?.priceUsd.toFixed(2)} USD / year
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => domain?.domain && handleBuyDomain(domain.domain)}
                      variant="outline"
                      className="px-6"
                    >
                      Buy
                    </Button>
                  </div>
                ))}

                {/* Pagination */}
                {searchResults.total > 10 && (
                  <div className="flex items-center justify-center gap-2 pt-4">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleSearch(undefined, currentPage - 1)}
                      disabled={currentPage === 1 || loading}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="text-sm text-muted-foreground">
                      Page {currentPage}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleSearch(undefined, currentPage + 1)}
                      disabled={!searchResults.hasNextPage || loading}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Empty State */}
          {suggestions.length === 0 && (
            <Card>
              <CardContent className="py-12">
                <div className="text-center">
                  <p className="text-muted-foreground">No domain suggestions available</p>
                  <p className="text-sm text-muted-foreground mt-1">Try searching for a different domain</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
