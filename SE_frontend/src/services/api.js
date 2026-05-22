const API_BASE_URL = "http://127.0.0.1:8001";

function getCurrentUserId() {
  return localStorage.getItem("currentUserId");
}

export async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(text || `Request failed: ${response.status}`);
  }

  if (!text) {
    return null;
  }

  return JSON.parse(text);
}

/* Auth */
export function getLoginUsers() {
  return request("/api/auth/users");
}

export function loginUser(email, password) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export function registerUser(data) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/* Dashboard */
export function getDashboard() {
  return request("/api/dashboard");
}

/* Books */
export function getBooks() {
  return request("/api/books");
}

export function getBook(bookId) {
  return request(`/api/books/${bookId}`);
}

export function createBook(data) {
  return request("/api/books", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/* Sentences */
export function getBookSentences(bookId) {
  return request(`/api/books/${bookId}/sentences`);
}

export function createBookSentence(bookId, data) {
  return request(`/api/books/${bookId}/sentences`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/* Comments */
export function getSentenceComments(sentenceId) {
  return request(`/api/sentences/${sentenceId}/comments`);
}

export function createSentenceComment(sentenceId, content) {
  const currentUser = JSON.parse(localStorage.getItem("currentUser") || "{}");

  return request(`/api/sentences/${sentenceId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      content,
      user_name: currentUser.name || "Guest User",
    }),
  });
}

export function likeComment(commentId) {
  return request(`/api/comments/${commentId}/like`, {
    method: "POST",
  });
}

/* Scraps */
export function getScraps() {
  return request("/api/scraps");
}

export function createScrap(sentenceId) {
  return request("/api/scraps", {
    method: "POST",
    body: JSON.stringify({
      sentence_id: sentenceId,
    }),
  });
}

export function deleteScrap(scrapId) {
  return request(`/api/scraps/${scrapId}`, {
    method: "DELETE",
  });
}

/* Authors */
export function getAuthors() {
  return request("/api/authors");
}

export function getAuthor(authorId) {
  return request(`/api/authors/${authorId}`);
}

export function createAuthor(data) {
  return request("/api/authors", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateAuthor(authorId, data) {
  return request(`/api/authors/${authorId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteAuthor(authorId) {
  return request(`/api/authors/${authorId}`, {
    method: "DELETE",
  });
}

/* My Page */
export function getMyPage() {
  const userId = getCurrentUserId();
  const query = userId ? `?user_id=${userId}` : "";

  return request(`/api/me${query}`);
}

export function updateMyPage(data) {
  const userId = getCurrentUserId();
  const query = userId ? `?user_id=${userId}` : "";

  return request(`/api/me${query}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
/* Playlists */
export function getPlaylists() {
  return request("/api/playlists");
}

export function createPlaylist(data) {
  const currentUser = JSON.parse(localStorage.getItem("currentUser") || "{}");

  return request("/api/playlists", {
    method: "POST",
    body: JSON.stringify({
      title: data.title,
      description: data.description,
      creator_name: currentUser.name || "Guest User",
    }),
  });
}

export function addPlaylistSong(playlistId, data) {
  return request(`/api/playlists/${playlistId}/songs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function likePlaylistSong(songId) {
  return request(`/api/playlist-songs/${songId}/like`, {
    method: "POST",
  });
}

export function deletePlaylistSong(songId) {
  return request(`/api/playlist-songs/${songId}`, {
    method: "DELETE",
  });
}

export function deletePlaylist(playlistId) {
  return request(`/api/playlists/${playlistId}`, {
    method: "DELETE",
  });
}
/* Music Search API */
export function searchMusic(keyword) {
  return request(`/api/music/search?q=${encodeURIComponent(keyword)}&limit=10`);
}
export function updateMyPassword(data) {
  const userId = localStorage.getItem("currentUserId");
  const query = userId ? `?user_id=${userId}` : "";

  return request(`/api/me/password${query}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}