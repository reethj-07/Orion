import { redirect } from "next/navigation";

/**
 * Landing route redirects users into the primary dashboard experience.
 */
export default function Home() {
  redirect("/dashboard");
}
