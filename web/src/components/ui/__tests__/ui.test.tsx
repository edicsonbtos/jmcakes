import { describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { render } from "@/test/utils";
import { ApiError } from "@/lib/errors";
import {
  BalanceFigure,
  Button,
  ConfirmDialog,
  DataTable,
  FilterChips,
  MoneyText,
  SearchField,
  Sheet,
  StatusPill,
  Stepper,
  TextField,
  useToast,
} from "..";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => "/admin" }));

describe("Button", () => {
  it("mientras carga queda deshabilitado y lo anuncia", () => {
    render(<Button loading>Registrar abono</Button>);
    const b = screen.getByRole("button", { name: "Registrar abono" });
    expect(b).toBeDisabled();
    expect(b).toHaveAttribute("aria-busy", "true");
  });
});

describe("MoneyText y BalanceFigure", () => {
  it("muestra los Bs que manda la API y 'Bs —' sin tasa", () => {
    const { rerender } = render(<MoneyText usd="97.00" ves="17964.40" />);
    expect(screen.getByText("$97,00")).toBeInTheDocument();
    expect(screen.getByText("Bs 17.964,40")).toBeInTheDocument();
    rerender(<MoneyText usd="12.00" ves={null} />);
    expect(screen.getByText("Bs —")).toHaveAttribute("title", "Sin tasa del día");
  });

  it("dice Debe, A favor o Al día según el signo del saldo", () => {
    const { rerender } = render(<BalanceFigure balance="97.00" balanceVes="17964.40" />);
    expect(screen.getByText("Debe")).toBeInTheDocument();
    expect(screen.getByText("$97,00")).toBeInTheDocument();
    rerender(<BalanceFigure balance="-4.00" />);
    expect(screen.getByText("A favor")).toBeInTheDocument();
    expect(screen.getByText("$4,00")).toBeInTheDocument();
    rerender(<BalanceFigure balance="0.00" />);
    expect(screen.getByText("Al día")).toBeInTheDocument();
  });

  it("anima el monto solo cuando cambia", () => {
    const { rerender } = render(<BalanceFigure balance="97.00" />);
    expect(screen.getByText("$97,00").className).not.toContain("animate-amount-in");
    rerender(<BalanceFigure balance="77.00" />);
    expect(screen.getByText("$77,00").className).toContain("animate-amount-in");
  });
});

describe("controles", () => {
  it("StatusPill siempre lleva texto", () => {
    render(<StatusPill tone="debt">Vencido $61,00</StatusPill>);
    expect(screen.getByText("Vencido $61,00")).toBeInTheDocument();
  });

  it("TextField asocia la etiqueta y anuncia el error", () => {
    render(<TextField label="Referencia" error="Esa referencia ya fue registrada." />);
    const input = screen.getByLabelText("Referencia");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Esa referencia ya fue registrada.");
  });

  it("FilterChips marca la opción activa con aria-pressed", async () => {
    const onChange = vi.fn();
    render(
      <FilterChips
        label="Filtrar clientes"
        value="todos"
        onChange={onChange}
        options={[
          { value: "todos", label: "Todos" },
          { value: "vencidos", label: "Vencidos" },
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: "Todos" })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: "Vencidos" }));
    expect(onChange).toHaveBeenCalledWith("vencidos");
  });

  it("SearchField limpia la búsqueda", async () => {
    const onValueChange = vi.fn();
    render(<SearchField label="Buscar cliente" value="0414" onValueChange={onValueChange} />);
    await userEvent.click(screen.getByRole("button", { name: "Limpiar búsqueda" }));
    expect(onValueChange).toHaveBeenCalledWith("");
  });

  it("Stepper suma y resta sin float y no baja de 0", async () => {
    const onChange = vi.fn();
    const { rerender } = render(<Stepper label="Canilla" value="2.5" onChange={onChange} />);
    expect(screen.getByLabelText("Cantidad de Canilla")).toHaveValue("2,5");
    await userEvent.click(screen.getByRole("button", { name: "Agregar uno: Canilla" }));
    expect(onChange).toHaveBeenLastCalledWith("3.5");
    await userEvent.click(screen.getByRole("button", { name: "Quitar uno: Canilla" }));
    expect(onChange).toHaveBeenLastCalledWith("1.5");
    rerender(<Stepper label="Canilla" value="0" onChange={onChange} />);
    expect(screen.getByRole("button", { name: "Quitar uno: Canilla" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Cantidad de Canilla"), { target: { value: "1,25" } });
    expect(onChange).toHaveBeenLastCalledWith("1.25");
  });
});

describe("Sheet y ConfirmDialog", () => {
  it("Sheet abre como diálogo con su título y se cierra", async () => {
    const onClose = vi.fn();
    render(
      <Sheet open onClose={onClose} title="Registrar abono">
        contenido
      </Sheet>,
    );
    expect(screen.getByRole("dialog", { name: "Registrar abono" })).toHaveAttribute("open");
    await userEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("ConfirmDialog exige el motivo y la opción antes de confirmar", async () => {
    const onConfirm = vi.fn(async () => {});
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        title="Revertir abono"
        confirmLabel="Revertir"
        reason={{}}
        choices={[
          { value: "ENTRY_ERROR", label: "Me equivoqué al registrarlo" },
          { value: "BANK_RETURN", label: "El banco lo devolvió" },
        ]}
        onConfirm={onConfirm}
      />,
    );
    const confirm = screen.getByRole("button", { name: "Revertir" });
    expect(confirm).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Motivo (obligatorio)"), "Lo cargué dos veces");
    expect(confirm).toBeDisabled();
    await userEvent.click(screen.getByLabelText("Me equivoqué al registrarlo"));
    expect(confirm).toBeEnabled();
    await userEvent.click(confirm);
    expect(onConfirm).toHaveBeenCalledWith({ reason: "Lo cargué dos veces", choice: "ENTRY_ERROR" });
  });

  it("ConfirmDialog muestra el detail de la API si falla", async () => {
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        title="Anular fiado"
        confirmLabel="Anular"
        reason={{}}
        onConfirm={async () => {
          throw new ApiError(409, "Esta deuda ya fue anulada.", "INVALID_STATE");
        }}
      />,
    );
    await userEvent.type(screen.getByLabelText("Motivo (obligatorio)"), "Error");
    await userEvent.click(screen.getByRole("button", { name: "Anular" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Esta deuda ya fue anulada.");
  });
});

describe("DataTable", () => {
  const rows = [{ id: "a", name: "Canilla" }];
  const columns = [{ key: "n", header: "Producto", render: (r: { name: string }) => r.name }];

  it("pide la página siguiente con el cursor", async () => {
    const onLoadMore = vi.fn();
    render(<DataTable caption="Productos" rows={rows} columns={columns} rowKey={(r) => r.id} nextCursor="cur-2" onLoadMore={onLoadMore} />);
    expect(screen.getByRole("table", { name: "Productos" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Cargar más" }));
    expect(onLoadMore).toHaveBeenCalledWith("cur-2");
  });

  it("sin cursor no ofrece más; sin filas muestra el vacío", () => {
    const { rerender } = render(<DataTable caption="Productos" rows={rows} columns={columns} rowKey={(r) => r.id} nextCursor={null} onLoadMore={() => {}} />);
    expect(screen.queryByRole("button", { name: "Cargar más" })).toBeNull();
    rerender(<DataTable caption="Productos" rows={[] as typeof rows} columns={columns} rowKey={(r) => r.id} empty={<p>Sin productos todavía</p>} />);
    expect(screen.getByText("Sin productos todavía")).toBeInTheDocument();
  });
});

describe("Toast", () => {
  function Trigger() {
    const t = useToast();
    return <button onClick={() => t.show("Abono de $20,00 registrado")}>avisar</button>;
  }

  it("anuncia la confirmación y desaparece sola", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<Trigger />);
    fireEvent.click(screen.getByRole("button", { name: "avisar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Abono de $20,00 registrado");
    act(() => {
      vi.advanceTimersByTime(4000);
    });
    await waitFor(() => expect(screen.queryByText("Abono de $20,00 registrado")).toBeNull());
  });
});
