// recharts usa ResizeObserver para medir contenedores; jsdom no lo incluye
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock
