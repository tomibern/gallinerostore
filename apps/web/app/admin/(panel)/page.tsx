import { redirect } from "next/navigation";

import { ADMIN_HOME } from "@/lib/admin-paths";

// La portada del panel es Productos (en el celular no hay otra).
export default function AdminHome() {
  redirect(ADMIN_HOME);
}
