import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ClimaService {

  private apiUrl = 'http://localhost:8000/clima';
  private historicoUrl = 'http://localhost:8000/clima/historico';

  constructor(private http: HttpClient) {}

  obtenerClima() {
    console.log('Conectando a:', this.apiUrl);
    return this.http.get(this.apiUrl);
  }

  obtenerHistorico() {
    console.log('Conectando a:', this.historicoUrl);
    return this.http.get(this.historicoUrl);
  }
}