import { describe, expect, it } from "vitest";

import { MIN_PASSWORD_LENGTH } from "./admin-paths";
import {
  PASSWORD_CHANGE_CLOSED,
  passwordChangeError,
  passwordChangeReducer,
  type PasswordChange,
} from "./password-change";
import { t } from "./texts";

const DONE: PasswordChange = {
  open: false,
  feedback: { kind: "done", text: t("admin.account.done") },
};

describe("passwordChangeReducer", () => {
  it("arranca cerrado y sin avisos", () => {
    expect(PASSWORD_CHANGE_CLOSED).toEqual({ open: false, feedback: null });
  });

  it("abrir muestra el formulario y borra el aviso anterior", () => {
    expect(passwordChangeReducer(DONE, { type: "open" })).toEqual({ open: true, feedback: null });
  });

  it("cancelar cierra el formulario y descarta el error", () => {
    const withError = passwordChangeReducer(
      passwordChangeReducer(PASSWORD_CHANGE_CLOSED, { type: "open" }),
      { type: "failed", text: "Mal" },
    );
    expect(passwordChangeReducer(withError, { type: "cancel" })).toEqual(PASSWORD_CHANGE_CLOSED);
  });

  it("al guardar bien se cierra y queda la confirmación", () => {
    const open = passwordChangeReducer(PASSWORD_CHANGE_CLOSED, { type: "open" });
    expect(passwordChangeReducer(open, { type: "saved" })).toEqual(DONE);
  });

  it("con un error sigue abierto y lo muestra", () => {
    const open = passwordChangeReducer(PASSWORD_CHANGE_CLOSED, { type: "open" });
    expect(passwordChangeReducer(open, { type: "failed", text: "Mal" })).toEqual({
      open: true,
      feedback: { kind: "error", text: "Mal" },
    });
  });
});

describe("passwordChangeError", () => {
  it("elige el texto del diccionario según lo que respondió la API", () => {
    expect(passwordChangeError("wrong_current")).toBe(t("admin.account.wrongCurrent"));
    expect(passwordChangeError("too_short")).toBe(
      t("admin.password.tooShort", { min: MIN_PASSWORD_LENGTH }),
    );
    expect(passwordChangeError("error")).toBe(t("admin.login.error"));
  });
});
