import numpy as np
import matplotlib.pyplot as plt

""" senoidal natural """
# numeros de puntos 
n = 36

# Generar un periodo completo

x = np.linspace(0, 2*np.pi, n)
y = np.sin(x)+1

# Graficar
plt.plot(x, y, 'bo-', label='Seno (1 periodo)')
plt.title('Un periodo de la funcion seno (36 puntos)')
plt.xlabel('x (radianes)')
plt.ylabel('sin(x)')
plt.grid(True)
plt.legend()
plt.show()
  

"""Grafica de Gaussiano"""

# Parametros
n = 36                # numero de muestras
mu = 0                # media
sigma = 0.1           # desviación estándar

# Ruido gaussiano blanco
noise = np.random.normal(mu, sigma, n)

# Graficar
plt.plot(noise, color='blue')
plt.axhline(0, color='lime', linewidth=2)
plt.grid(True, color='red', linestyle='-')
plt.title("White Gaussian Noise")
plt.show()


""" senales combinada """

y_total = y + noise 

# Graficar resultados
plt.figure(figsize = (8,5))

plt.plot(x, y, 'b--', label='Seno puro')
plt.plot(x, noise, color='gray', alpha=0.5, label='Ruido gaussiano')
plt.plot(x, y_total, 'r-', linewidth=2, label='Seno + Ruido')

plt.title('Seno con Ruido Gaussiano (36 puntos)')
plt.xlabel('x (radianes)')
plt.ylabel('Amplitud')
plt.legend()
plt.grid(True)
plt.show()
