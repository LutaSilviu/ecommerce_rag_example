# Nexo Market — copy pentru comanda demonstrativă

Acest document definește textul și regulile de afișare pentru plata și comanda demonstrativă. Comanda este doar o înregistrare de prototip: nu reprezintă o achiziție reală și nu se retrag bani.

## Texte UI

### Alegerea plății — checkout

- **Titlu:** Metodă de plată
- **Opțiune:** Plată simulată (prototip)
- **Explicație, vizibilă lângă opțiune:** Aceasta este o simulare. Nu se procesează nicio plată și nu ți se vor cere date de card.
- **Text de ajutor sub secțiune:** Comanda va fi salvată doar ca înregistrare demonstrativă în contul tău.

Nu se afișează câmpuri pentru numărul cardului, data expirării, CVV, PIN sau alte credențiale de plată.

### Revizuirea comenzii — înainte de confirmare

- **Titlu secțiune:** Revizuiește comanda demonstrativă
- **Etichetă plată:** Plată simulată (neprocesată)
- **Notificare persistentă, înaintea butonului final:** Aceasta este o comandă de test. Confirmarea creează o înregistrare demonstrativă; nu se efectuează nicio plată și nu vei fi taxat(ă).
- **Buton final:** Confirmă comanda demonstrativă
- **Text secundar lângă buton, dacă spațiul permite:** Fără plată reală

Notificarea și eticheta plății trebuie să apară în același ecran cu acțiunea de confirmare, fără să fie ascunse într-un tooltip, într-un link sau într-o secțiune restrânsă.

### Confirmare

- **Titlu:** Comanda demonstrativă a fost înregistrată
- **Mesaj:** Comanda ta de test a fost salvată în cont. Nu s-a efectuat nicio plată și nu ai fost taxat(ă).
- **Etichetă stare plată:** Plată simulată — neprocesată
- **Detaliu comandă:** Numărul comenzii: {orderNumber}
- **Acțiuni:** Vezi comenzile mele · Continuă cumpărăturile

Folosește starea „înregistrată” pentru comanda de prototip; nu afișa mesaje precum „plată reușită”, „plată aprobată” sau „achiziție finalizată”.

### Istoricul contului și detaliile comenzii

- **Etichetă vizibilă pe fiecare comandă de prototip:** Comandă demonstrativă
- **Stare plată:** Plată simulată — neprocesată
- **Explicație, la detalii:** Înregistrare de prototip. Nu a fost procesată nicio plată.

Păstrează eticheta „Comandă demonstrativă” vizibilă atât în rândul din istoric, cât și în pagina de detalii.

## Reguli consecvente de afișare

1. Explică natura simulată la selectarea metodei, repetă explicația în revizuirea finală și confirmă explicit lipsa unei plăți după trimitere.
2. Nu folosi singure cuvinte precum „Plătește”, „Plată reușită” sau „Achită acum” pentru etichete, butoane ori stări.
3. Nu solicita și nu stoca date de card sau credențiale de plată. Nu include un furnizor de plăți ori o siglă de card care ar sugera o tranzacție reală.
4. Starea comenzii și starea plății sunt distincte: înregistrarea demonstrativă poate exista, dar plata rămâne întotdeauna „simulată — neprocesată”.
5. Folosește aceleași texte și aceeași stare în sumar, confirmare, istoric și detaliile comenzii; păstrează etichetele în română.
