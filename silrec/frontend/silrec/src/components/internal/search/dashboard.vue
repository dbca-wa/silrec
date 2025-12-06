<template>
    <div class="container-fluid" id="SearchDashboard">
        <h1 class="my-4">Search</h1>
        
<!--
        <div class="row">
            <div class="col-md-12 mb-4">
                <SearchByUser />
            </div>
        </div>
-->
        
        <div class="row mt-5">
            <div class="col-md-12">
                <SearchByText />
            </div>
        </div>
    </div>
</template>

<script>
//import SearchByUser from '@/components/internal/search/search_by_user.vue';
import SearchByText from '@/components/internal/search/search_by_text.vue';

export default {
    name: 'SearchDashboard',
    components: {
        //SearchByUser,
        SearchByText
    },
    data() {
        return {
            activeTab: 'user'
        };
    }
};
</script>

<style scoped>
#SearchDashboard {
    padding: 20px;
}
</style>
