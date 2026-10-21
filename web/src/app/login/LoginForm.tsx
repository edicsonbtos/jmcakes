"use client";

import { useActionState, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button, IconButton, InlineAlert, TextField } from "@/components/ui";
import { login, type LoginState } from "./actions";

/** Formulario de login (`useActionState` + Server Action). Sin JS también envía. */
export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState<LoginState, FormData>(login, null);
  const [show, setShow] = useState(false);

  return (
    <form action={action} className="flex flex-col gap-5" noValidate>
      <input type="hidden" name="next" value={next} />
      <TextField
        label="Teléfono"
        name="phone"
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        placeholder="0414-123.45.67"
        defaultValue={state?.phone ?? ""}
        required
        size="lg"
        autoFocus
      />
      <TextField
        label="Contraseña"
        name="password"
        type={show ? "text" : "password"}
        autoComplete="current-password"
        required
        size="lg"
        suffix={
          <IconButton
            label={show ? "Ocultar contraseña" : "Mostrar contraseña"}
            onClick={() => setShow((v) => !v)}
            className="size-11"
          >
            {show ? <EyeOff aria-hidden className="size-5" /> : <Eye aria-hidden className="size-5" />}
          </IconButton>
        }
      />
      {state?.error ? <InlineAlert tone="error">{state.error}</InlineAlert> : null}
      <Button type="submit" size="lg" fullWidth loading={pending}>
        Entrar
      </Button>
    </form>
  );
}
