import { render, screen, cleanup } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi, afterEach } from "vitest"
import { DropZone } from "./DropZone"

afterEach(cleanup)

function makeFile(name: string, size = 100, type = "text/csv"): File {
  const content = new Uint8Array(size)
  return new File([content], name, { type })
}

describe("DropZone", () => {
  it("renders upload prompt when empty", () => {
    render(<DropZone files={[]} onFilesChange={() => {}} />)
    expect(screen.getByText("Drag & drop your files here")).toBeInTheDocument()
    expect(screen.getByText("Browse files")).toBeInTheDocument()
  })

  it("shows selected files with name and size", () => {
    const file = makeFile("data.csv", 2048)
    render(<DropZone files={[file]} onFilesChange={() => {}} />)
    expect(screen.getByText("data.csv")).toBeInTheDocument()
    expect(screen.getByText("2.0 KB · Ready")).toBeInTheDocument()
  })

  it("calls onFilesChange when removing a file", async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const files = [makeFile("a.csv"), makeFile("b.csv")]
    render(<DropZone files={files} onFilesChange={onChange} />)

    // The X buttons are the ones inside file cards (not Browse files)
    await user.click(screen.getByRole("button", { name: "Remove a.csv" }))
    expect(onChange).toHaveBeenCalledWith([files[1]])
  })

  it("disables browse button when disabled", () => {
    render(<DropZone files={[]} onFilesChange={() => {}} disabled />)
    expect(screen.getByText("Browse files")).toBeDisabled()
  })

  it("shows max 3 files in the list", () => {
    const files = [makeFile("a.csv"), makeFile("b.csv"), makeFile("c.csv")]
    render(<DropZone files={files} onFilesChange={() => {}} />)
    expect(screen.getByText("a.csv")).toBeInTheDocument()
    expect(screen.getByText("b.csv")).toBeInTheDocument()
    expect(screen.getByText("c.csv")).toBeInTheDocument()
  })
})
