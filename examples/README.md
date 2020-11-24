## Interesting SPARQL queries:

### Terms and their definition if it exists.

    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
    SELECT ?k_label ?k_definition ?k_subject ?language
            WHERE {{
            ?k_subject skos:prefLabel ?k_label .
            BIND (lang(?k_label) AS ?language)
            OPTIONAL {{
                ?k_subject skos:definition ?k_definition .
            
                FILTER (
                lang(?k_definition) = 'en'
    
                )
            }}
        
            FILTER (
                lang(?k_label) = 'en'
    
                )
            }}
            ORDER BY ?k_label
            
### Find the similar terms that were added to the RDF. 
         
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT DISTINCT (?k_label1 AS ?term_1) (?k_label2 as ?term_2) ?score ?word1 ?word2
        WHERE {
            ?subject <word> ?word1 .
            ?subject <word> ?word2 .
            FILTER (
                ?word1 != ?word2
            )
            ?subject <score> ?score .
            ?word1 skos:prefLabel ?k_label1 .
            ?word2 skos:prefLabel ?k_label2 .
            FILTER (
                lang(?k_label1) = 'en' &&
                lang(?k_label2) = 'en' &&
                UCASE(str(?k_label1)) < UCASE(str(?k_label2))
            )
        }
        
      ORDER BY DESC(?score)

### Definitions (and their term)

(Deprecated)

    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
    SELECT ?k_label ?k_definition ?language ?k_subject
            WHERE {{
            ?k_subject skos:prefLabel ?k_label .
            ?k_subject skos:definition ?k_definition .
    
            BIND (lang(?label) AS ?language)
    
            FILTER (
                lang(?k_label) = 'en' &&
                lang(?k_definition) = 'en' 
                )
            }}
            ORDER BY ?k_label
            
      
