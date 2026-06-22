import { Component, ChangeDetectorRef, OnInit, AfterViewInit, ViewChild, ElementRef, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ClimaService } from '../services/clima.service';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
  encapsulation: ViewEncapsulation.None
})
export class AppComponent implements OnInit, AfterViewInit {
  @ViewChild('graficaTemperatura') graficaCanvas!: ElementRef<HTMLCanvasElement>;
  chart: Chart | null = null;
  viewReady = false;
  clima: any = null;
  historico: any[] = [];

  horaActual: string = '';
  cargando = true;
  error = '';

  constructor(private climaService: ClimaService, private cdr: ChangeDetectorRef) {}

  crearGrafica() {
    // Diagnostic logs
    console.log('crearGrafica() called — viewReady:', this.viewReady);
    console.log('graficaCanvas (ElementRef):', this.graficaCanvas);

    if (!this.viewReady || !this.graficaCanvas?.nativeElement) {
      console.warn('Canvas no disponible aún');
      return;
    }

    const canvasEl = this.graficaCanvas.nativeElement as HTMLCanvasElement;
    console.log('canvas element:', canvasEl);
    console.log('canvas.width:', canvasEl.width, 'canvas.height:', canvasEl.height);
    console.log('canvas.offsetWidth:', canvasEl.offsetWidth, 'canvas.offsetHeight:', canvasEl.offsetHeight);

    const ctx = canvasEl.getContext('2d');
    if (!ctx) {
      console.error('No se pudo obtener el contexto del canvas');
      return;
    }

    if (this.chart) {
      this.chart.destroy();
    }

    // Robust mapping: accept multiple possible field names from backend
    const first = this.historico && this.historico.length ? this.historico[0] : null;
    console.log('primer registro historico:', first);

    const mapFecha = (r: any) => r?.fecha ?? r?.fecha_registro ?? r?.hora_consulta ?? r?.date ?? r?.timestamp ?? null;
    const mapTemp = (r: any) => r?.temperatura ?? r?.temp ?? r?.temperature ?? r?.t ?? null;

    const etiquetas = this.historico.map((r: any) => {
      const v = mapFecha(r);
      // Normalize to string for labels
      return v instanceof Date ? v.toLocaleString() : (v ?? '').toString();
    });

    const temperaturas = this.historico.map((r: any) => mapTemp(r));

    console.log('etiquetas (primeras 10):', etiquetas.slice(0, 10));
    console.log('temperaturas (primeras 10):', temperaturas.slice(0, 10));

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: etiquetas,
        datasets: [
          {
            label: 'Temperatura °C',
            data: temperaturas,
            borderWidth: 2,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            display: true,
            title: { display: true, text: 'Fecha' },
            ticks: { maxRotation: 45, autoSkip: true },
          },
          y: {
            display: true,
            title: { display: true, text: 'Temperatura (°C)' },
          },
        },
      },
    });
    console.log('Canvas:', this.graficaCanvas);
console.log('Etiquetas:', etiquetas.length);
console.log('Temperaturas:', temperaturas.length);
console.log('Primer registro:', this.historico[0]);

}

  ngAfterViewInit(): void {
    this.viewReady = true;
    if (this.historico.length) {
      this.crearGrafica();
    }
  }
  ngOnInit(): void {
    this.horaActual = new Date().toLocaleTimeString('es-PE');

    this.climaService.obtenerClima().subscribe({
      next: (data: any) => {
        console.log('✅ DATOS RECIBIDOS:', data);
        this.clima = data;
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('❌ ERROR EN PETICIÓN:', err);
        this.error = 'No se pudo cargar el clima. Asegúrate de que el backend esté funcionando en http://localhost:8000';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });

    this.climaService.obtenerHistorico().subscribe({
      next: (data: any) => {
        console.log('📊 HISTORICO:', data);
        this.historico = data;
        // Intentar crear la gráfica inmediatamente; crearGrafica
        // comprobará `viewReady` y esperará al ngAfterViewInit si es necesario.
        this.crearGrafica();
      },
      error: (err: any) => {
        console.error('❌ ERROR HISTÓRICO:', err);
      }
    });

    setInterval(() => {
      this.horaActual = new Date().toLocaleTimeString('es-PE');
      this.cdr.detectChanges();
    }, 1000);
  }
}
