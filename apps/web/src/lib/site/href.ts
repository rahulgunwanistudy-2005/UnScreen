import type { ResolvedPathname } from '$app/types';

/** A resolved app path with a query string appended (resolve() takes no query). */
export function withQuery(path: ResolvedPathname, query: string): ResolvedPathname {
	return `${path}?${query}` as ResolvedPathname;
}
