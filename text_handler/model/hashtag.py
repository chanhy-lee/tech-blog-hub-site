import re
from math import ceil, floor
from typing import List, Tuple

from llamaapi import LlamaAPI

# CAUTION : get_preprocessed_text를 통해 얻어진 텍스트에 맞춰 함수 작성 -> 해당 함수 return 형식이 달라지면 버그 발생 가능성 있음
# from preprocessed import get_preprocessed_text
from fewshot_examples import *
from text_processing_utils import TextProcessingUtils
from llm_request_utils import LLMRequestUtils

class HashtaggingModule:
    def __init__(self, api_token):
        self.text_process_utils = TextProcessingUtils()
        self.llm_utils = LLMRequestUtils()
        self.llama = LlamaAPI(api_token=api_token)
    
    def run_llm_request(self, prompt: str, token_label: str = "Token") -> List[str]:
        # LLM 요청을 보내고 응답에서 키워드를 추출하는 Helper 함수 (token_label로 요청 구분)
        api_request_json = self.llm_utils.make_request_json(prompt)
        response = self.llama.run(api_request_json=api_request_json)
        response_json = response.json()

        print(f"{token_label} USAGE:", response_json['usage'])  # Token 추적용

        return response_json['choices'][0]['message']['content'].split(', ')


    def get_keywords_from_intro(self, intro_blocks: List[List[Tuple[str, str]]]) -> List[str]:
        """
        Intro에 해당하는 block들을 받아 LLM을 통해 keywords를 추출하는 함수입니다.

        Parameters:
        intro_blocks (List[List[Tuple[str, str]]]): Intro에 해당하는 block들
        
        Returns:
        List[str]: LLM 모델이 선정한 keywords 리스트
        """
        final_prompt = self.llm_utils.make_prompt_for_intro_blocks(intro_blocks=intro_blocks)
        return self.run_llm_request(final_prompt, token_label="INTRO TOKEN")


    def get_candidates_from_block(self, body_block: List[Tuple[str, str]]) -> List[str]:
        """
        body에 해당하는 특정 block을 입력받아 LLM을 통해 keywords를 추출하는 함수입니다.

        Parameters:
        body_block (List[Tuple[str, str]]): 분석하고자 하는 body에 해당하는 block
        
        Returns:
        List[str]: LLM 모델이 선정한 keywords 리스트
        """
        final_prompt = self.llm_utils.make_prompt_for_unit_block(body_block=body_block)
        return self.run_llm_request(final_prompt, token_label="BLOCK TOKEN")


    def make_keywords_from_candidates(self, candidates: List[str]) -> List[str]:
        """
        여러 block들에서 모아진 keywords들(candidates)를 받아 LLM을 통해 적절한 keywords만을 재추출하는 함수입니다.

        Parameters:
        candidates (List[str]): 기존의 여러 block들에서 추출된 keywords들이 모인 리스트
        
        Returns:
        List[str]: LLM 모델이 선정한 keywords 리스트
        """
        final_prompt = self.llm_utils.make_prompt_for_candidates(candidates)
        return self.run_llm_request(final_prompt, token_label="CANDIDATES TOKEN")


    # CAUTION - Not currently used : generate_hashtags에 사용되지는 않은 함수, body에서 keywords를 잘 뽑아내는 지 중간 테스트용으로 사용
    def get_keywords_from_body(self, body: List[List[Tuple[str, str]]]) -> List[str]:
        """
        body 부분에 해당되는 block들을 입력받아, LLM을 통해 적절한 keywords을 재추출하는 함수입니다.
        (반드시, body 부분에 해당되는 blocks list만 입력받아야 합니다.)

        Parameters:
        body (List[List[Tuple[str, str]]]): 전처리된 텍스트에서 body에 해당되는 block들의 list
        
        Returns:
        List[str]: LLM 모델이 선정한 keywords 리스트
        """
        total_candidates = []
        for block in body:
            candidates = self.get_candidates_from_block(block)
            total_candidates = total_candidates + candidates
        
        print("TOTAL CANDIDATES:",total_candidates)

        return self.make_keywords_from_candidates(total_candidates)


    def get_keywords_from_category(self, keywords: List[str]) -> List[str]:
        """
        keywords를 입력받아, keywords의 내용을 바탕으로 하여
        category json에 정의된 active한 분류 중 적절한 분류를 추출하는 함수

        Parameters:
        keywords (List[str]) : 사전추출이 완료된 핵심단어 리스트
        
        Returns:
        result (List[str]) : category에 정의된 분류 중, 적절한 분류 리스트
        """
        final_prompt = self.llm_utils.make_prompt_for_category(keywords)
        return self.run_llm_request(final_prompt, token_label="CATEGORY TOKEN")

    
    def dedup_list(self, keywords:List[str]) -> List[str]:
        # keywords 내에 동일한 글자를 가진 단어가 여러개라면, 한 단어만 남기고 나머지를 제거하는 함수입니다.
        # 함수의 예시는 다음과 같습니다: ["machine learning, MachineLearning", "Deep Learning"] -> ["machine Learning", "Deep Learning"]
        dedup_dict = {}
        for word in keywords:
            standard_word = word.lower().replace(" ", "")
            if standard_word not in dedup_dict:
                dedup_dict[standard_word] = word
        
        return list(dedup_dict.values())


    def postprocess_keywords(self, keywords: List[str]) -> List[str]:
        """
        get_keywords 계열 함수를 통해 얻어진 keywords를 모아, 후처리하여 최종 해시태그 리스트를 반환하는 함수입니다.

        Parameters:
        keywords (List[str]): 해시태그로 추출될 최종 후보군
        
        Returns:
        List[str]: 후처리된 keywords (= 최종 해시태그)
        """
        cleaned_keywords = keywords  # 초기 입력 keywords를 클린업하여 저장할 변수

        # 이상 단어 제거
        # Intro 이상 단어 제거 (현재 버그 미발견 상태)
        # Body 이상 단어 제거 (현재 버그 미발견 상태)
        # Category 이상 단어 제거
        cleaned_keywords = [
            re.sub(r'Category: ', '', word) if "Category:" in word else word 
            for word in cleaned_keywords
        ]

        # 블랙리스트 단어 제거
        blacklist = ["Kurly", "TechBlog", "Blog"]
        filtered_keywords = [word for word in cleaned_keywords if word not in blacklist]

        # LLM에 보내기 전에, 키워드가 비어 있을 경우 대비
        if not filtered_keywords:
            filtered_keywords.append("Experience Article")

        # 중복 키워드 제거
        unique_keywords = self.dedup_list(filtered_keywords)

        # 의미적으로 동일한 키워드 제거 (ex. AI & Artificial Intelligence)
        final_prompt = self.llm_utils.make_prompt_for_postprocess(unique_keywords)
        processed_keywords = self.run_llm_request(final_prompt, token_label="POSTPROCESS TOKEN")

        # 형식 변환 (Camel Case로 변환)
        final_hashtags = self.text_process_utils.to_camel_case(processed_keywords)

        return final_hashtags


    def generate_hashtags(self, html_text: str) -> List[str]:
        """
        전처리된 텍스트를 받아 해시태그를 추출하는 함수입니다.

        Parameters:
        html_text (str): 전처리된 html text
        
        Returns:
        hashtags (List[str]): 추출된 해시태그 list
        """
        parsed_list = self.text_process_utils.make_blocks_from_preprocessed_text(html_text)
        print("Length of parsed list :", len(parsed_list))  # CAUTION: 실제 추출에 사용되는 block 개수와 다를 수 있습니다.
        
        NUM_PARAGRAPHS_TRESHOLD = 5 # 어떤 이유로 파싱에 실패하거나, 글의 길이가 짧은 경우에 해당하는 최소 문단 수
        FOOTER_RATIO = 0.1  # 글의 마지막 부분 중 분석에서 제외할 비율 (마무리나 글쓴이의 프로필 정보 등 불필요한 부분)
        n = len(parsed_list)
        footer_length = ceil(FOOTER_RATIO * n)
        extract_ratio = 0.6 # body_part에서 추출할 비율

        intro_keywords, candidates, body_keywords, category_keywords = [], [], [], []

        if n < NUM_PARAGRAPHS_TRESHOLD:
            # intro_keywords = [] (intro_keywords는 추출 생략)
            extracted_part = max(parsed_list, key=lambda x: len(x[1][1])) # 가장 긴 block에 대하여 추출
            if extracted_part[0][0] != 'Title':
                title = parsed_list[0][0][1]
                extracted_part = [('Subtitle', f"{title}, {extracted_part[0][1]}"), extracted_part[1]]
            body_keywords = self.get_candidates_from_block(extracted_part)
            candidates = body_keywords # 후보군 = 가장 긴 block의 keywords로 대체
        else:
            intro_part = parsed_list[:2]
            body_part = parsed_list[2:-footer_length]
            
            intro_keywords = self.get_keywords_from_intro(intro_part)
            body_part = self.text_process_utils.make_merged_block_list(body_part)

            b = ceil(extract_ratio * len(body_part))
            extracted_part = sorted(body_part, key=lambda x: len(x[1][1]), reverse=True)[:b]
            for block in extracted_part:
                candidates.extend(self.get_candidates_from_block(block))
            body_keywords = self.make_keywords_from_candidates(candidates=candidates)
        
        # candidates를 통해 category 선정
        category_keywords = self.get_keywords_from_category(candidates)

        print("Intro HashTags:", intro_keywords)
        print("Body Hashtags:", body_keywords)
        print("Category Hashtags:", category_keywords)

        hashtags = self.dedup_list(self.postprocess_keywords(intro_keywords + body_keywords) + category_keywords)

        return hashtags