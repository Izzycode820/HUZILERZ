"use client";

import { ApolloProvider } from "@apollo/client/react";
import { themeClient } from "@/services/graphql/clients";

export default function ShowcaseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ApolloProvider client={themeClient}>
      {children}
    </ApolloProvider>
  );
}
