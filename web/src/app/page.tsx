import { redirect } from "next/navigation";

/** La raíz lleva al panel; `proxy.ts` decide si hace falta entrar primero. */
export default function Home() {
  redirect("/admin");
}
