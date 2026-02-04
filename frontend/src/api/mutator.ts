export const customFetch = async <T>(
  url: string,
  options: RequestInit
): Promise<T> => {
  const rawBaseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!rawBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not set.");
  }
  const baseUrl = rawBaseUrl.replace(/\/+$/, "");
  const response = await fetch(`${baseUrl}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error("Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};
