import { handlers } from "@/auth";

// Route handlers win over next.config rewrites, so /api/auth/* stays local
// while every other /api/* path is proxied to the RepoPilot API.
export const { GET, POST } = handlers;
