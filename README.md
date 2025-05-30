# Automatisation de Rendus avec Husk (Karma/KarmaXPU)

Cette application facilite et automatise les rendus avec Husk en utilisant les moteurs Karma ou KarmaXPU. Elle propose une interface graphique pour configurer vos rendus, les ajouter à une file d’attente, et exécuter plusieurs rendus en séquence.

---

## 📥 Télécharger l'exécutable
**Téléchargez la dernière version ici** :  
[📥 Télécharger maintenant](https://github.com/Maxime272003/husk-app/releases/latest/download/husk-app.exe)

---

## Fonctionnalités principales
- **Rendu unique** : Lancez un rendu unique en sélectionnant une scène USD et les paramètres de rendu.
- **File d'attente** : Ajoutez plusieurs configurations de rendu à une file d'attente et exécutez-les en séquence.
- **Types de rendu** :
  - `Full Sequence` : Rendu de toutes les images d'une plage définie (`husk --frame 1-120 ...`).
  - `FML` : Rendu de trois images : la première, celle du milieu et la dernière (`husk --frame-list 1 60 120 ...`).
- **Aperçu de la commande** : Visualisez la commande exacte qui sera exécutée pour chaque rendu dans la file d’attente.
- **Choix du moteur** : Sélection rapide entre Karma et KarmaXPU via des boutons radio.

---

## Prérequis
### Logiciels nécessaires
- **Husk** : Assurez-vous que Husk est installé et accessible dans votre PATH.
- **Karma/KarmaXPU** : Les moteurs de rendu doivent être disponibles avec Husk.

### Dépendances Python
- **PyQt5** : Installez avec la commande :
  ```bash
  pip install PyQt5
  ```

---

## Installation et utilisation
### Étapes d'installation
#### Option 1 : Utilisation du fichier exécutable
1. Téléchargez le fichier `.exe` généré dans le dossier `dist/` (disponible après le build).
2. Exécutez le fichier `.exe` directement pour lancer l'application.

#### Option 2 : Construire l'application vous-même
1. Clonez ou téléchargez ce projet dans un répertoire local :
   ```bash
   git clone https://github.com/Maxime272003/husk-app.git
   cd husk-app
   ```
2. Installez les dépendances nécessaires :
   ```bash
   pip install PyQt5
   ```
3. Générez un fichier exécutable avec PyInstaller :
   ```bash
   pyinstaller --onefile ./husk-app.py
   ```
4. Le fichier exécutable sera généré dans le dossier `dist/`.
5. Lancez le fichier `.exe` généré pour utiliser l'application.

---

## Utilisation de l'application
### Rendu unique
1. Remplissez les champs nécessaires :
   - Chemin de la scène USD (`*.usd`, `*.usda`, `*.usdc`).
   - Frame de début et de fin.
   - Résolution en pourcentage.
   - Choix du moteur de rendu (Karma ou KarmaXPU).
2. Sélectionnez le type de rendu (`Full Sequence` ou `FML`).
3. Cliquez sur **Lancer**.

### File d'attente
1. Configurez un rendu en suivant les étapes du rendu unique.
2. Cliquez sur **Ajouter à la file d'attente**.
3. Répétez pour ajouter plusieurs rendus.
4. Cliquez sur **Lancer** pour exécuter tous les rendus de la file d'attente.

### Gestion de la file d'attente
- Pour supprimer un rendu, sélectionnez-le dans la liste et cliquez sur **Supprimer le rendu sélectionné**.
- Chaque rendu affiche un aperçu de la commande Husk qui sera exécutée.

---

## Logs et diagnostics
Les messages relatifs aux rendus (commandes, succès, erreurs) sont affichés dans la section des logs de l'application. Utilisez ces informations pour diagnostiquer les problèmes si nécessaire.

---

## Contribution
Les contributions sont les bienvenues ! N'hésitez pas à soumettre des pull requests ou à signaler des problèmes.

---

## Licence
Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus d'informations.